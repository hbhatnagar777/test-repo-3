# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to Laptop in AdminConsole
LaptopMain : This class provides methods for Laptop related operations

Class:

    LaptopMain()

Functions:

get_client_name_from_hostname     : To get the client name from the host name

__validate_install                  : To validate install on the client machine

check_if_laptop_added               : Method to check whether laptop appears in the Solutions->Laptop page

add_new_windows_laptop              : calls method to add windows laptop from laptops page

add_new_mac_aptop()                 : Method to add mac laptop to laptops page

deactivate_laptop()                 : Method to deactivate laptop from laptops page

update_software()                   : Method to update software from laptops page

check_readiness()                   : Method to perform check readiness

send_logs()                         : Method to perform action send logs

retire_client()                     : Method to retire the client

activate_laptop()                   : Method to activate laptop by user selection

perform_backup_now()                : call the method to perform backup

validate_backup_after_deactivation() : validation of the backup after deactivation

covert_size_to_mb()                  : convert given the size to MB

auto_trigger_backupjob()             : Auto trigger backup job when subclient content added

__get_backup_details()               : Read the current backup details from adminconsole

__get_client_details()               : Retrieve client details from DB

validate_laptop_listing_page()       : method to validates the laptop listing page details for newly installed laptop

validate_laptop_summaryinfo()        : method to Validates the laptop summary info of the laptop page

set_validation_values()              : Set the validation values for laptop

validate_laptop_details()            : Validates the values displayed for client against values provided as input

subclient_restore()                  : validate laptop restore

view_jobs_validation()               : method to access and valdate view jobs option from details page

action_click()                       : method to click on empty page to move cursor from selected action list 

"""

import datetime
import math
import inspect
import time
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from AutomationUtils import logger
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.options_selector import OptionsSelector
from Server.JobManager.jobmanager_helper import JobManager
from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.Laptop.Laptops import Laptops
from Web.AdminConsole.Laptop.LaptopDetails import LaptopDetails
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.Common.exceptions import CVWebAutomationException
from Install.install_validator import InstallValidator
from Laptop.CloudLaptop import cloudlaptophelper

class LaptopMain:
    """Admin console helper for Laptop operations"""

    def __init__(self, admin_page, commcell, csdb=None):
        """
        Helper for Laptop related files

        Args:
            admin_page  (object)   --  AdminPage class object

        """
        self.commcell = commcell
        self.csdb = csdb
        self.__admin_console = admin_page
        self.__driver = admin_page.driver
        self.__table = Table(admin_page)
        self.__rtable = Rtable(admin_page)
        self.__laptops = Laptops(admin_page)
        self.__jobs = Jobs(self.__admin_console)
        self.__navigator = admin_page.navigator
        self.__backup = Backup(admin_page)
        self.__ida_utils = CommonUtils(commcell)
        self.__utility = OptionsSelector(commcell)
        self.__job_manager = JobManager(commcell=commcell)
        self.__rpanel = RPanelInfo(self.__admin_console)
        self.__laptop_details = LaptopDetails(admin_page, commcell=commcell)
        self.log = logger.get_log()
        self._validate = None
        self._host_name = None
        self._client_name = None
        self._user_name = None
        self._password = None
        self._confirm_password = None
        self._activation_user = None
        self._activation_plan = None
        self._machine_object = None
        self._source_dir = None
        self._subclient_obj = None
        self._configured_status = 'Configured'
        self._configuration_status = 'Active'
        self._sla_status = 'Met'
        self._sla_reason = 'Protected'
        self._tags = 'No tags'
        self._last_offline_time = 'Not Applicable'
        self._days_until_retired = 'Not Applicable'
        self._days_until_deleted = 'Not Applicable'
        
        
    @property
    def host_name(self):
        """ Get host_name"""
        return self._host_name

    @host_name.setter
    def host_name(self, value):
        """ Set host_name"""
        self._host_name = value

    @property
    def client_name(self):
        """ Get client_name"""
        return self._client_name

    @client_name.setter
    def client_name(self, value):
        """ Set client_name"""
        self._client_name = value

    @property
    def user_name(self):
        """ Get user name """
        return self._user_name

    @user_name.setter
    def user_name(self, value):
        """ Set user_name """
        self._user_name = value

    @property
    def password(self):
        """ Get password"""
        return self._password

    @password.setter
    def password(self, value):
        """ Set password"""
        self._password = value

    @property
    def confirm_password(self):
        """ Get confirm_password"""
        return self._password

    @confirm_password.setter
    def confirm_password(self, value):
        """ Set confirm_password"""
        self._confirm_password = value

    @property
    def activation_user(self):
        """ Get activate_user"""
        return self._activation_user

    @activation_user.setter
    def activation_user(self, value):
        """ Set activate_user"""
        self._activation_user = value

    @property
    def activation_plan(self):
        """ Get activation_plan"""
        return self._activation_plan

    @activation_plan.setter
    def activation_plan(self, value):
        """ Set activation_plan"""
        self._activation_plan = value

    @property
    def machine_object(self):
        """ Get machine_object"""
        return self._machine_object

    @machine_object.setter
    def machine_object(self, value):
        """ Set machine_object"""
        self._machine_object = value

    @property
    def source_dir(self):
        """ Get source data directory"""
        return self._source_dir

    @source_dir.setter
    def source_dir(self, value):
        """ Set source data directory"""
        self._source_dir = value

    @property
    def tenant_company(self):
        """ Get Tenant Company"""
        return self._tenant_company

    @tenant_company.setter
    def tenant_company(self, value):
        """ Set Tenant Company"""
        self._tenant_company = value
        
    @property
    def email(self):
        """ Get email"""
        return self._email

    @email.setter
    def email(self, value):
        """ Set email"""
        self._email = value

        
    def __validate_install(self, client_name):
        """ To validate install on the client machine"""
        self._validate = InstallValidator(client_name, self)
        self._validate.validate_sp_version()
        self._validate.validate_baseline()
        self._validate.validate_services()

    def client_deactivation_validation(self,):
        """ client deactivation validation"""
        
        self.__rtable.search_for(self._client_name)
        client_details= self.__rtable.get_table_data()
        status = self.__laptops.get_client_configuration_status('Deconfigured')
        if not status is True:
            exp = "Client {0} status is not showing correctly after deactivation".format(self._client_name)
            self.log.exception(exp)
            raise Exception(exp)

        if 'No plan is associated' not in client_details['Plans'][0]:
            exp = "Client {0} is still associated to plan after deactivation".format(self._client_name)
            self.log.exception(exp)
            raise Exception(exp)
        
        grid_list = self.__rtable.get_grid_actions_list(self._client_name)
        if 'Activate' not in grid_list or 'Deactivate' in grid_list:
            exp = "deactivate button is still showing from actions"
            self.log.exception(exp)
            raise Exception(exp)
            

    def client_activation_validation(self, plan_name):
        """ client activation validation"""

        self.__rtable.search_for(self._client_name)
        client_details= self.__rtable.get_table_data()

        status = self.__laptops.get_client_configuration_status('Configured')
        if not status is True:
            exp = "Client {0} status is not showing correctly after activation".format(self._client_name)
            self.log.exception(exp)
            raise Exception(exp)
        
        if not plan_name in client_details['Plans'][0]:
            exp = "Client {0} is not associated to plan after activation".format(self._client_name)
            self.log.exception(exp)
            raise Exception(exp)
        
        grid_list = self.__rtable.get_grid_actions_list(self._client_name)
        if 'Activate' in grid_list or 'Deactivate' not in grid_list:
            exp = "Activate button is showing instead of deactivate when laptop activated"
            self.log.exception(exp)
            raise Exception(exp)


    def check_if_laptop_added(self):
        """ Method to check whether laptop appears in the Solutions->Laptop page """
        self.__navigator.navigate_to_devices()
        if not self.__table.is_entity_present_in_column("Name", self._client_name):
            exp = "Laptop with Given client name {0} does not exist"\
                .format(self._client_name)
            self.log.exception(exp)
            raise Exception(exp)

    def add_new_windows_laptop(self):
        """calls method to add windows laptop from laptops page"""
        self.__navigator.navigate_to_devices()
        job_id = self.__laptops.add_windows_laptop(self.host_name,
                                                   self.user_name,
                                                   self.password,
                                                   self.confirm_password)
        self.log.info("Job %s is started to add new WINDOWS laptop", job_id)
        job_details = self.__jobs.job_completion(job_id)
        if not job_details['Status'] == 'Completed':
            exp = "Add windows laptop job {0} is not completed successfully for machine {1}"\
                    .format(job_id, self.host_name)
            self.log.exception(exp)
            raise Exception(job_details)
        self.check_if_laptop_added()
        self.log.info('New windows laptop is added successfully')

    def add_new_mac_laptop(self):
        """calls method to add mac laptop from laptops page"""
        self.__navigator.navigate_to_devices()
        job_id = self.__laptops.add_mac_laptop(self.host_name,
                                               self.user_name,
                                               self.password,
                                               self.confirm_password)
        self.log.info("Job %s is started to add new MAC laptop", job_id)
        job_details = self.__jobs.job_completion(job_id)
        if not job_details['Status'] == 'Completed':
            exp = "Add Mac laptop job {0} is not completed successfully for machine {1}"\
                    .format(job_id, self.host_name)
            self.log.exception(exp)
            raise Exception(job_details)
        self.check_if_laptop_added()
        self.log.info('New MAC laptop is added successfully')

    def deactivate_laptop(self):
        """calls method to deactivate laptop from laptops page"""
        self.__laptops.deactivate_laptop(self._client_name)
        self.log.info("Client {0} deactivated successfully".format(self._client_name))

    def update_software(self, reboot=False):
        """calls method to update software from laptops page"""
        self.__navigator.navigate_to_devices()
        job_id = self.__laptops.action_update_software(self._client_name, reboot=reboot)
        self.log.info("Job %s is started for update software", job_id)
        job_details = self.__jobs.job_completion(job_id)
        if not job_details['Status'] == 'Completed':
            exp = "Update Software job {0} is not completed for client {1}"\
                    .format(job_id, self._client_name)
            self.log.exception(exp)
            raise Exception(job_details)
        self.__validate_install(self._client_name)
        self.log.info("Successfully updated the client {0}".format(self._client_name))

    def check_readiness(self):
        """calls method to perform check readiness"""
        self.__navigator.navigate_to_devices()
        self.__laptops.action_check_readiness(self._client_name)
        self.log.info("Check readiness completed successfully for client {0}"\
                      .format(self._client_name))

    def retire_client(self):
        """calls method to retire the client"""
        self.__navigator.navigate_to_devices()
        job_id = self.__laptops.action_retire_client(self._client_name)
        self.log.info("Job %s is started to retire the client", job_id)
        job_details = self.__jobs.job_completion(job_id)
        if not job_details['Status'] == 'Completed':
            exp = "Retire client job {0} is not completed for client {1}"\
                    .format(job_id, self._client_name)
            self.log.exception(exp)
            raise Exception(job_details)
        self.log.info("Retire client operation completed Successfully for the client {0}"\
                        .format(self._client_name))

    def activate_laptop(self, plan_name=None):
        """method to activate the laptop by user selection"""
        if plan_name:
            self.__laptops.activate_laptop_byplan(self._client_name, plan_name)
        else:
            self.__laptops.activate_laptop_byuser(self._client_name)
        
    def navigate_to_laptops_page(self, tab_text='Laptop'):
        """ method used to navigate to particular tab in devices page based on text"""
        
        self.log.info("Navigating to [{0}] tab in laptop page " .format(tab_text))
        self.__navigator.navigate_to_devices()
                    
    def perform_backup_now(self, suspend_resume=False, **kwargs):
        """method to perform backup """
        #------- BACKUP FROM ACTIONS--------#
        if kwargs.get('backup_type') == 'backup_from_actions':
            job_id  = self.__laptops.backup_from_actions(self._client_name, self.__backup.BackupType.INCR)

        #------- BACKUP FROM DETAILS--------#
        elif kwargs.get('backup_type') == 'backup_from_detailspage':
            job_id = self.__laptops.backup_from_detailspage(self._client_name, self.__backup.BackupType.INCR)
        
        if suspend_resume:
            self.log.info("*****Verification of Suspend and resume backup for the client [{0}]*****"\
                      .format(self._client_name))
            
            self.__laptops.suspend_job_from_detailspage()
            jobobj = self.commcell.job_controller.get(job_id=job_id)
            self.__job_manager.job = jobobj
            self.__job_manager.wait_for_state('suspended')
            self.__laptops.resume_job_from_detailspage()
            self.__job_manager.wait_for_state('completed')

        else:
            jobobj = self.commcell.job_controller.get(job_id=job_id)
            self.__job_manager.job = jobobj
            self.__job_manager.wait_for_state('completed')
            job_details = self.__jobs.job_completion(job_id)
            if not job_details['Status'] == 'Completed':
                exp = "Backup job [{0}] is not completed for client [{1}]"\
                        .format(job_id, self._client_name)
                self.log.exception(exp)
                raise Exception(job_details)
        self.log.info("***** Backup job completed Successfully for the client {0} *****"\
                      .format(self._client_name))
        return job_id


    def validate_backup_after_deactivation(self):
        """call the method to validate able trigger backup after deactivation"""
        #----- validating backup from actions
        try:
            job_id  = self.__laptops.backup_from_actions(self._client_name, self.__backup.BackupType.INCR)
        except Exception as err:
            self.log.info("As Expected ! Unable to trigger INCREMENTAL job for deactivated client")
            self.log.info(err)
        else:
            if job_id:
                exp = "INCREMENTAL job {0} triggered for deactivated client from laptop actions{1}"\
                        .format(job_id, self._client_name)
                self.log.exception(exp)
                raise Exception(exp)
        
        #----- validating backup from details page

        try:
            job_id  = self.__laptops.backup_from_detailspage(self._client_name, self.__backup.BackupType.INCR)
        except Exception as err:
            self.log.info("As Expected ! Unable to trigger INCREMENTAL job for deactivated client from details page")
            self.log.info(err)
        else:
            if job_id:
                exp = "INCREMENTAL job {0} triggered for deactivated client from details page {1}"\
                        .format(job_id, self._client_name)
                self.log.exception(exp)
                raise Exception(exp)

    @staticmethod
    def covert_size_to_mb(backup_size, backup_units):
        "convert given the size to MB"

        if backup_units == 'KB':
            new_backup_size = float(backup_size) /1024
        elif backup_units == 'MB':
            new_backup_size = float(backup_size)
        elif backup_units == 'GB':
            new_backup_size = float(backup_size)*1024
        else:
            new_backup_size = float(backup_size) /(1024*1024)
        return new_backup_size

    def auto_trigger_backupjob(self, options=None):
        """ Auto trigger backup job when subclient content added"""

        # Add new content with required size to default subclient of this client and run incremental backup
        #DEFAULT_FILE_SIZE = 2500 KB
        self.log.info("Add new content with required size and run the incremental job on this client")
        self._subclient_obj = self.__ida_utils.get_subclient(self._client_name)
        self._source_dir = self.__utility.create_directory(self._machine_object)
        self.log.info("Adding directory to subclient content with: {0}".format(self._source_dir))
        if not options==None:
            self._subclient_obj.content += [self.__utility.create_test_data(self._machine_object, self._source_dir, options=options)]
        else:
            self._subclient_obj.content += [self.__utility.create_test_data(self._machine_object, self._source_dir)]

        #----------- Wait for auto triggered backups-------#
        self.log.info("Wait for auto triggered backup job after content added")
        jobs = self.__job_manager.get_filtered_jobs(
            self._client_name,
            time_limit=30,
            retry_interval=5,
            backup_level='Incremental',
            current_state='Running'
            )
        jobid = jobs[1][0]
        jobobj = self.commcell.job_controller.get(job_id=jobid)
        return jobobj, jobid

    def __get_backup_details(self, displayed_val):
        """ Retrieve client backup details from the client"""
        
        #-------------------------------------------------------------------------------------
        #validation of client properties#
        #    Last Backup Time  - Compare with Start Time of the last backup job
        #    Last Backup Size  - Compare with Size of Application of the last backup job
        #    Application size - Get the existing Application size from adminconsole +
        #                        add the specified amount of data (For Ex: 2 mb) + run incr backup.
        #                        Application size must be updated with new value
        #-------------------------------------------------------------------------------------


        self.log.info("Read the current Application  size from adminconsole")
        total_backup = displayed_val

        backupsize_and_time = {}
        backup_size_unit = total_backup.split()
        backup_size = backup_size_unit[0]
        backup_units = backup_size_unit[1]
        #------- convert the backup size into "MB" --------#
        current_total_backup = self.covert_size_to_mb(backup_size, backup_units)
        jobobj, _joid = self.auto_trigger_backupjob()
        
        #----------- read the last backup time and size from above triggered job --------#
        full_job_details = jobobj.details
        sub_dict = full_job_details['jobDetail']['detailInfo']
        backupsize_and_time['Last backup time'] = sub_dict.get('startTime')
        #------last backup size of the incr bakup job
        backupsize_and_time['Last Backup Size'] = int(sub_dict.get('sizeOfApplication'))
        backupsize_and_time['Last job status'] = jobobj.status
         
        #-----get the Last backup size from last job convert to adminconsole display format--------#
        #----------- Read the folder size which intern returns in "MB"---------#
        self.log.info("get the last backup size from last backup job ")
        last_backupsize_after_conversion = self.covert_size_to_mb(backupsize_and_time['Last Backup Size'], 'bytes')
        backupsize_and_time['Application size'] = current_total_backup + last_backupsize_after_conversion

        
        return  backupsize_and_time
    
    def get_client_details(self, client_obj, client_region=False):
        """ Retrieve client details from DB"""
        try:

            # Check client version in app_clientprop
            client_name = client_obj.client_name
            client_id = client_obj.client_id
            client_details={}
            query = """select attrval from app_clientprop where componentnameid = {0}
                    and attrname in ('Client Version','SP Version and Patch Info')""".format(client_id)
            resultset = self.__utility.exec_commserv_query(query)
            value01 = resultset[0][0].split("(")[0]
            value02 = resultset[0][1].split(":")[1]
            if ',' in value02:
                value02 = value02.split(',')[0]
                
            client_version = str(value01) + '.' + str(value02)
            client_details['Version'] = client_version
            self.log.info("Laptop [{0}] version in app_clientprop [{1}]".format(client_name, client_version))
            
            # Check install date in app_clientprop
            query = """Select created from app_clientprop where componentnameid = {0}
                        and attrname = 'Installation Company ID' """.format(client_id)
            
            resultset = self.__utility.exec_commserv_query(query)
            _client_install_date = datetime.datetime.fromtimestamp(int(resultset[0][0]))
            client_install_date = _client_install_date.strftime('%b %#d, %#I:%M %p')
            client_details['Install date'] = client_install_date
            
            self.log.info(
                "Laptop [{0}] install_date in app_clientprop [{1}]".format(client_name, client_install_date)
            )
            
            # Check client last online in  CCRClientToClient
            query = """select lastOnlineTime from CCRClientToClient where FromClientId =2 
                       and ToClientId = {0}""".format(client_id) 
            resultset = self.__utility.exec_commserv_query(query)
            _client_online_time = datetime.datetime.fromtimestamp(int(resultset[0][0]))
            client_online_time = _client_online_time.strftime('%b %#d, %#I:%M %p')
            client_details['Last online time'] = client_online_time
            
            self.log.info(
                "Laptop [{0}] Last online time in CCRClientToClient [{1}]".format(client_name, client_online_time)
            )
            
            if client_region:
                query = """ select regionId from App_EntityRegionAssoc where entitytype=3 
                           and entityId= {0} and flags&2 = 2""".format(client_id)

                region_id = self.__utility.exec_commserv_query(query)
                query01 = """ select name from app_region where id = {0}""".format(region_id[0][0])
                region_name = self.__utility.exec_commserv_query(query01)
                client_details['Workload region'] = region_name[0][0]
                self.log.info(
                    "Laptop [{0}] Workload region id in App_EntityRegionAssoc [{1}]".format(client_name, region_id[0][0])
                )
            
            return client_details
        
        except Exception as excp:
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))
    
    def validate_laptop_listing_page(self):
        """validates the laptop listing page details for newly installed laptop"""
        try:
            self.__rtable.access_link(self._client_name)
            laptop_summary_dict = RPanelInfo(self.__admin_console, 'Summary').get_details()
            backup_info = self.__get_backup_details(laptop_summary_dict['Application size'])
            total_backup_size = backup_info['Application size']
            backup_time = datetime.datetime.fromtimestamp(int(backup_info['Last backup time']))
            last_backup_time = backup_time.strftime('%b %#d, %#I:%M %p')
            clientobject = self.commcell.clients.get(self._client_name)
            client_details = self.get_client_details(clientobject)
            user_name = self._activation_user.split("\\")[1]
            
            validation_dict = {
             'Name':[self._client_name],
             'Owners':[self._activation_user],
             'User name':[user_name],
             'Email':[self._email],
             #'Configured':[self._activation_status],
             'Version':[client_details['Version']],
             'Install date':[client_details['Install date']],
             'Last backup':[last_backup_time],
             'Last job status':[backup_info['Last job status']],
             'Application size':[total_backup_size],
             'Plans':[self._activation_plan],
             'SLA status': [self._sla_status], 
             'SLA reason':[self._sla_reason],
             'Last successful backup':[last_backup_time],
             'Last online time':[client_details['Last online time']],
             'Last offline time':[self._last_offline_time],
             'Days until retired':[self._days_until_retired],
             'Days until deleted':[self._days_until_deleted],
             'Tags':[self._tags]
             }
            
            
            #----------- get the latest info from adminconsole after backup--------#
            # moving between overview and laptop tabs to see the updated values from listing page after incr backup
            # But Don't hard refresh the page for updated values
            #----------------------------------------------------------------------#
            self.navigate_to_laptops_page()
            self.__rtable.search_for(self._client_name)
            self.__rtable.click_grid_reset_button()
            visible_columns = self.__rtable.get_visible_column_names()
            hidden_colum_list=[]
    
            for dict_key, dict_val in validation_dict.items():
                if dict_key not in visible_columns:
                    hidden_colum_list.append(dict_key)
            self.__rtable.display_hidden_column(hidden_colum_list)
            table_data = self.__rtable.get_table_data()
            #--- Owners column data is not showing correctly by default when default columns selected
            # as column width is shrinked to get the correct text hiding most of the default columns from display     
            if not self._activation_user in table_data['Owners']:
                self.__rtable.click_grid_reset_button()
                visible_columns.remove('Actions')
                hide_colums_from_display=[]
                hide_colums_from_display=visible_columns[4:]
                self.__rtable.hide_selected_column_names(hide_colums_from_display)
            owner_data = self.__rtable.get_table_data()
            table_data['Owners']=owner_data['Owners']
    
            #----------- validation of the data from laptop listing page--------#
            for dict_key, dict_val in validation_dict.items():
                self.log.info('validation values "{0}"'.format(dict_val))
                if dict_key == 'Application size':
                    #------- convert the current Application size into "MB" --------#
                    total_backupsize_before_convertion = table_data[dict_key]
                    temp_sizeunit_list = total_backupsize_before_convertion[0].split()
                    backup_size = temp_sizeunit_list[0]
                    backup_units = temp_sizeunit_list[1]
                    total_backupsize_after_convertion = self.covert_size_to_mb(backup_size, backup_units)
                    validation_val = math.trunc(dict_val[0])
                    total_backupsize_after_convertion = math.trunc(total_backupsize_after_convertion)
                    
                    if total_backupsize_after_convertion >= validation_val:
                        self.log.info("'Application size' {0} updated with correct value after backup" .format(
                            total_backupsize_after_convertion))
                    else:
                        exp = "'Application size' {0} does not updated correctly".format(
                            total_backupsize_after_convertion)
                        raise Exception(exp)
                
                elif dict_key == 'Last online time':
                    display_time = table_data[dict_key]
                    validation_time = dict_val
                    if display_time == validation_time:
                        self.log.info("Last seen online time updated correctly")
                    
                    elif display_time >= validation_time:
                        display_time_object = datetime.datetime.strptime(display_time[0], '%b %d, %I:%M %p')
                        validation_time_object = datetime.datetime.strptime(validation_time[0], '%b %d, %I:%M %p')
                        time_diff = display_time_object - validation_time_object
                        if time_diff.seconds<=180:
                            self.log.info("Last seen online time updated correctly")
                        else:
                            exp = "Last seen online time {0} not updated correctly ".format(display_time)
                            self.log.exception(exp)
                            raise Exception(exp)           
                    else:
                        exp = "Last seen online time {0} not updated correctly ".format(display_time)
                        self.log.exception(exp)
                        raise Exception(exp)           
                else:
                    if dict_val == table_data[dict_key]:
                        self.log.info("displayed value {0} matches with given value {1}".format(
                            table_data[dict_key], dict_val))
    
                    else:
                        exp = "displayed value {0} does not match with given value {1} for column: {2}".format(
                            table_data[dict_key], dict_val, dict_key)
                        raise Exception(exp)
                
        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))
        finally:
            self.__rtable.search_for(self._client_name)
            self.__rtable.click_grid_reset_button()
    

    def set_validation_values(self, displayed_val):
        """Set the validation values for laptop """

        #-------------------------------------------------------------------------------------
        #validation of client properties#
        #    Last Backup Time  - Compare with Start Time of the last backup job
        #    Last Backup Size  - Compare with Size of Application of the last backup job
        #    Application size - Get the existing Application size from adminconsole +
        #                        add the specified amount of data (For Ex: 2 mb) + run incr backup.
        #                        Application size must be updated with new value
        #    Last Seen online - X - Get Last seen online time from Adminconsole page
        #                       Restart services on on client
        #                       Go to laptop page and comeback but [Do not Refresh the Adminconsole Page]
        #                       Y- Get the updated time from Adminconsole page
        #                       Compare Y>X
        #    #---Last seen online time updates for every 24 hours from CCR tables,
        #    #--- to update the value immediately restart the CVD on client machine ------#
        #-------------------------------------------------------------------------------------

        #-----------get the last backup size from last backup job and convert into MBS--------#
        backup_info = self.__get_backup_details(displayed_val['Summary']['Application size'])
        total_backupsize = backup_info['Application size']
        #-----get the Last backup size from last job convert to adminconsole display format--------#
        self.log.info("get the last backup size from last backup job ")
        last_backup_size_before_convertion = backup_info['Last Backup Size']
        last_backupsize_after_conversion = self.covert_size_to_mb(last_backup_size_before_convertion, 'bytes')
        i = int(math.floor(math.log(last_backupsize_after_conversion, 1024)))
        power = math.pow(1024, i)
        last_backupsize = round(last_backupsize_after_conversion / power, 2)

        #-----get the last backup time from last backup job and convert to adminconsole display format--------#
        backup_time = datetime.datetime.fromtimestamp(int(backup_info['Last backup time']))
        last_backup_time = backup_time.strftime('%b %#d, %#I:%M:%S %p')
        #-----------get the client last seen online time --------#
        self.log.info("get the laptop last seen online info from the laptop details page and restart the services")
        last_online_time = displayed_val['Summary']['Last seen online']
        #---Restart the client services ---#
        self.__ida_utils.restart_services([self._client_name])

        #-----------Create the dictionary with default values from laptop details page--------#
        default_values = {"Schedules": ['Incremental Automatic schedule',
                                        'Space Reclamation'],
                          "Content":['Desktop',
                                     'Documents',
                                     'Office',
                                     'Pictures',
                                     'Image',
                                     'MigrationAssistant'],
                          "Region":'Not set\nEdit'}


        validation_dict = {
            'Summary': {'Host Name': self._host_name,
                        'Last backup time': last_backup_time,
                        'Last backup size': last_backupsize,
                        'Application size': total_backupsize,
                        'Last seen online': last_online_time,
                        'Region': default_values["Region"]},
            'Security': [self._activation_user],
            'Schedules':default_values["Schedules"],
            'Content':default_values["Content"], #backup_info['Content'],
            'Plan': self._activation_plan,
        }

        for each_item in  backup_info['Content']:
            validation_dict['Content'].append(each_item)

        return validation_dict
    
    
    def validate_laptop_summary_tile(self):
        """Laptop details page summary tile validation"""
        self.__rtable.access_link(self._client_name)
        summary_dict = RPanelInfo(self.__admin_console, 'Summary').get_details()
        backup_info = self.__get_backup_details(summary_dict['Application size'])
        backup_time = datetime.datetime.fromtimestamp(int(backup_info['Last backup time']))
        last_backup_time = backup_time.strftime('%b %#d, %#I:%M %p')
        clientobject = self.commcell.clients.get(self._client_name)
        client_details = self.get_client_details(clientobject, client_region=True)
        self.log.info(client_details)
        #-----get the Last backup size from last job convert to adminconsole display format--------#
        self.log.info("get the last backup size from last backup job ")
        last_backup_size_before_convertion = backup_info['Last Backup Size']
        last_backupsize_after_conversion = self.covert_size_to_mb(last_backup_size_before_convertion, 'bytes')
        i = int(math.floor(math.log(last_backupsize_after_conversion, 1024)))
        power = math.pow(1024, i)
        last_backupsize = round(last_backupsize_after_conversion / power, 2)
        
        
        laptop_validation_dict = {
         'Host name':self._client_name,
         'Last backup time':last_backup_time,
         'Last backup size':last_backupsize,
         'Install date':client_details['Install date'],
         'Version':client_details['Version'],
         'Application size':backup_info['Application size'],
         'Configuration status':self._configuration_status ,
         'Last seen online':client_details['Last online time'],
         #'Next backup time':,
         'Plan':self._activation_plan,
         'Company':self._tenant_company,
         'Workload region':client_details['Workload region']
         }
        
        #read latest data from summary tile after inc job
        self.navigate_to_laptops_page()
        self.__rtable.access_link(self._client_name)
        laptop_summary_dict = RPanelInfo(self.__admin_console, 'Summary').get_details()
        
        #----------- validation of the data from laptop summary tile--------#
        for dict_key, dict_val in laptop_validation_dict.items():
            self.log.info('validation values "{0}"'.format(dict_val))
            if dict_key == 'Application size':
                #------- convert the current Application size into "MB" --------#
                total_backupsize_before_convertion = laptop_summary_dict[dict_key]
                temp_sizeunit_list = total_backupsize_before_convertion.split()
                backup_size = temp_sizeunit_list[0]
                backup_units = temp_sizeunit_list[1]
                total_backupsize_after_convertion = self.covert_size_to_mb(backup_size, backup_units)
                #validation_val = dict_val
                validation_val = math.trunc(dict_val)
                total_backupsize_after_convertion = math.trunc(total_backupsize_after_convertion)
                if total_backupsize_after_convertion >= validation_val:
                    self.log.info("'Application size' {0} updated with correct value after backup" .format(
                        total_backupsize_after_convertion))
                else:
                    exp = "'Application size' {0} does not updated correctly".format(
                        total_backupsize_after_convertion)
                    raise Exception(exp)
        
            elif dict_key == 'Last backup size':
                disp_val = laptop_summary_dict[dict_key]
                key_val = dict_val
                #------- convert the Last backup size into "MB" --------#
                temp_sizeunit_list = disp_val.split()
                backup_size = temp_sizeunit_list[0]
                backup_units = temp_sizeunit_list[1]
                last_backup_size_after_conversion = self.covert_size_to_mb(backup_size, backup_units)
                i = int(math.floor(math.log(last_backup_size_after_conversion, 1024)))
                power = math.pow(1024, i)
                last_backup_size = round(last_backup_size_after_conversion / power, 2)
                if last_backup_size == key_val:
                    self.log.info("'{0}' displayed value '{1}' match with validation value '{2}'"
                                    .format(disp_val, last_backup_size, key_val))
                else:
                    exp = "Last backup size {0} not updated correctly ".format(
                       laptop_summary_dict['dict_key'])
                    raise Exception(exp)
                
            elif dict_key == 'Last seen online':
                display_time = laptop_summary_dict[dict_key]
                validation_time = dict_val
                if display_time == validation_time:
                    self.log.info("Last seen online time updated correctly")
                    
                elif display_time >= validation_time:
                    display_time_object = datetime.datetime.strptime(display_time[0], '%b %d, %I:%M %p')
                    validation_time_object = datetime.datetime.strptime(validation_time[0], '%b %d, %I:%M %p')
                    time_diff = display_time_object - validation_time_object
                    if time_diff.seconds<=180:
                        self.log.info("Last seen online time updated correctly")
                    else:
                        exp = "Last seen online time {0} not updated correctly ".format(display_time)
                        self.log.exception(exp)
                        raise Exception(exp)           
                else:
                    exp = "Last seen online time {0} not updated correctly ".format(display_time)
                    self.log.exception(exp)
                    raise Exception(exp)   

            else:
                if dict_val == laptop_summary_dict[dict_key]:
                    self.log.info("displayed value {0} matches with given value {1}".format(
                        laptop_summary_dict[dict_key], dict_val))
        
                else:
                    exp = "displayed value {0} does not match with given value {1} for column: {2}".format(
                        laptop_summary_dict[dict_key], dict_val, dict_key)
                    raise Exception(exp)


    def validate_laptop_details(self):
        """
        Validates the values displayed for client against values provided as input
        """

        #----------- get the current  info from adminconsole after backup--------#
        current_displayed_val = self.__laptop_details.laptop_info(self._client_name)

        #----------- set the validation values based on current displayed values--------#
        validation_dict = self.set_validation_values(current_displayed_val)
        self.log.info("validation values: {0}".format(validation_dict))

        #----------- get the latest info from adminconsole after backup--------#

        displayed_val = self.__laptop_details.laptop_info(self._client_name)

        for key, value in displayed_val.items():
            if key == 'Content':
                for index, each_item in enumerate(value):
                    if ' MigrationAssistant\nUser defined' in each_item:
                        new_list = each_item.split('\n')
                        del displayed_val['Content'][index]
                        for eac_data in new_list:
                            if not eac_data == 'User defined':
                                displayed_val['Content'].append(eac_data)

                    elif 'Inherited from plan\nDesktop ' in each_item:
                        displayed_val['Content'][index] = 'Desktop'


        for key, value in displayed_val.items():
            if key == 'Content':
                for index, each_item in enumerate(value):
                    displayed_val['Content'][index] = each_item.strip()


        for key, value in validation_dict.items():
            #----------validation of fields with list of values---------#
            if isinstance(value, list):
                self.log.info('Entity given val %s', value)
                if  displayed_val[key] != "None" and validation_dict[key] != "None":
                    count = 0
                    validation_dict[key] = sorted(validation_dict[key])
                    max_val = max(len(displayed_val[key]), len(validation_dict[key]))
                    for  each_summary in sorted(displayed_val[key]):
                        if count < max_val:
                            if str(each_summary).strip() == validation_dict[key][count]:
                                self.log.info("{0} displayed for {1} matches"
                                              .format(each_summary, key))
                            else:
                                exp = "{0} displayed for {1} does not match \
                                with {2}".format(key, each_summary, validation_dict[key][count])
                                self.log.exception(exp)
                                raise Exception(exp)
                        else:
                            break
                        count += 1
            #----------validation of string fields ex:Plan  ---------#
            elif isinstance(value, str):
                if displayed_val[key] == validation_dict[key]:
                    self.log.info("{0} displayed for {1} matches with {2} given"
                                  .format(displayed_val[key], key, validation_dict[key]))
                else:
                    exp = "{0} displayed for {1} does not match with {2} given ".format(
                        displayed_val[key], key, validation_dict[key])
                    self.log.exception(exp)
                    raise Exception(exp)

            else:
                #----------validation of fields from Summary info---------#
                self.log.info('Entity given val :{0}'.format(value))
                for summary_key, summary_value in value.items():
                    if summary_key == 'Application size':
                        #------- convert the current Application size into "MB" --------#
                        total_backupsize_before_convertion = displayed_val[key][summary_key]
                        temp_sizeunit_list = total_backupsize_before_convertion.split()
                        backup_size = temp_sizeunit_list[0]
                        backup_units = temp_sizeunit_list[1]
                        total_backupsize_after_convertion = self.covert_size_to_mb(backup_size, backup_units)
                        if total_backupsize_after_convertion >= summary_value:
                            self.log.info("'Application size' {0} updated with correct value after backup" .format(
                                total_backupsize_after_convertion))
                        else:
                            exp = "'Application size' {0} does not updated correctly".format(
                                total_backupsize_after_convertion)
                            raise Exception(exp)

                    elif summary_key == 'Last seen online':
                        disp_val = displayed_val[key][summary_key]
                        key_val = validation_dict[key][summary_key]
                        if disp_val > key_val:
                            self.log.info("Last seen online time updated correctly")
                        else:
                            exp = "Last seen online time {0} not updated correctly ".format(summary_value)
                            self.log.exception(exp)
                            raise Exception(exp)

                    elif summary_key == 'Last backup size':
                        disp_val = displayed_val[key][summary_key]
                        key_val = validation_dict[key][summary_key]
                        #------- convert the Last backup size into "MB" --------#
                        temp_sizeunit_list = disp_val.split()
                        backup_size = temp_sizeunit_list[0]
                        backup_units = temp_sizeunit_list[1]
                        last_backup_size_after_conversion = self.covert_size_to_mb(backup_size, backup_units)
                        i = int(math.floor(math.log(last_backup_size_after_conversion, 1024)))
                        power = math.pow(1024, i)
                        last_backup_size = round(last_backup_size_after_conversion / power, 2)
                        if last_backup_size == key_val:
                            self.log.info("'{0}' displayed value '{1}' match with validation value '{2}'"
                                          .format(summary_key, last_backup_size, key_val))
                        else:
                            exp = "Last backup size {0} not updated correctly ".format(displayed_val[key][summary_key])
                            self.log.exception(exp)
                            raise Exception(exp)

                    else:
                        disp_val = displayed_val[key][summary_key]
                        key_val = validation_dict[key][summary_key]
                        if disp_val == key_val:
                            self.log.info("'{0}' displayed value '{1}' match with validation value '{2}'"
                                          .format(summary_key, disp_val, key_val))
                        else:
                            exp = "'{0}' displayed for '{1}' does not match with validation value '{2}' given".format(
                                summary_key, disp_val, key_val)
                            self.log.exception(exp)
                            raise Exception(exp)

    def subclient_restore(self, backup_jobid=None, tmp_path=None, cleanup=True, **kwargs):
        """validate laptop restore"""
        try:
            if tmp_path is None:
                dest_path = self.__utility.create_directory(self._machine_object)

            compare_source = self._source_dir
            compare_destination = dest_path
            if not self._machine_object.os_info == 'WINDOWS':
                self._machine_object.change_file_permissions(dest_path, 775)

            self.log.info(
                """
                Starting restore with source:[{0}],
                destination:[{1}],
                With restore option as : [{2}]
                """.format(self._source_dir, dest_path, kwargs.get('restore_type'))
                )
            #------- RESTORE FROM LAST BACKUP JOB--------#
            if kwargs.get('restore_type') == 'restore_from_job':
                restore_job_id = self.__laptops.restore_from_job(backup_jobid, self._source_dir, dest_path)
            #------- RESTORE FROM LAPTOP DETAILS PAGE--------#
            elif kwargs.get('restore_type') == 'restore_from_detailspage':
                restore_job_id = self.__laptops.restore_from_details_page(self._client_name, self._source_dir, dest_path)
            #------- RESTORE FROM ACTIONS--------#
            elif kwargs.get('restore_type') == 'restore_from_actions':
                restore_job_id = self.__laptops.restore_from_actions(self._client_name, self._source_dir, dest_path)

            job_details = self.__jobs.job_completion(restore_job_id)
            if job_details['Status'] == "Completed":
                self.log.info("Restore job [{0}] completed successfully".format(restore_job_id))
            else:
                raise Exception("Restore job [{0}] did not complete successfully".format(restore_job_id))

            #------- Validation for restored content --------#
            self.log.info("""Executing backed up content validation:
                        Source: [{0}], and
                        Destination [{1}]""".format(compare_source, compare_destination))

            result, diff_output = self._machine_object.compare_meta_data(compare_source, compare_destination)

            self.log.info("Performing meta data comparison on source and destination")
            if not result:
                self.log.error("Meta data comparison failed")
                self.log.error("Diff output: \n{0}".format(diff_output))
                raise Exception("Meta data comparison failed")
            self.log.info("Meta data comparison successful")

            self.log.info("Performing checksum comparison on source and destination")
            result, diff_output = self._machine_object.compare_checksum(compare_source, compare_destination)
            if not result:
                self.log.error("Checksum comparison failed")
                self.log.error("Diff output: \n{0}".format(diff_output))
                raise Exception("Checksum comparison failed")
            self.log.info("Checksum comparison successful")

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))
        finally:
            if cleanup:
                self.__utility.remove_directory(self._machine_object, dest_path)

    def delete_laptop(self, client_name):
        """delete the laptop client and validate"""
        notification = self.__laptops.delete_from_listingpage(client_name)
        if not 'is now deleted' in notification:
            raise CVWebAutomationException("Unexpected notification [{0}] when client deleted"
                                           .format(notification))
        #------- Validation of the client deletion--------#
        self.navigate_to_laptops_page()
        if self.__laptops.is_laptop_exists(client_name):
            raise CVWebAutomationException('Laptop is still showing from listing page after deleted')
        self.log.info('-------Laptop deleted successfully---------')
                        
    def view_jobs_validation(self, job_id):
        """validate job status from view jobs button """
        self.__laptops.access_view_jobs()
        self.__table.access_action_item(job_id, 'View job details')
        job_details_dict= self.__rpanel.get_details()
        if not job_details_dict['Status']== 'Completed':
            exp =  "Backup job [{0}] is not completed for client [{1}]"\
                    .format(job_id, self._client_name)
            self.log.exception(exp)
            raise Exception(job_details_dict)

        self.log.info('View job details validation completed successfully')

    def validate_listing_page_search(self, laptop_name):
        """Validate if a Laptop is listed"""
        self.__navigator.navigate_to_devices()
        if self.__laptops.is_laptop_exists(laptop_name):
            self.log.info('listing page search validation completed for the laptop device')
        else:
            raise CVWebAutomationException('Laptop device not listed in listing page')

    def edit_laptop_name(self, name, new_name):
        """Method to edit file server name"""
        self.__navigator.navigate_to_devices()
        self.__laptops.access_laptop(name)
        self.__laptop_details.change_laptop_name(new_name)

    def action_click(self):
        """ Method is used to press tab on listing page at any place to move out of action menu"""
        actions = ActionChains(self.__driver)
        actions.send_keys(Keys.TAB)
        actions.perform()
        time.sleep(10)

    def trigger_cloudlaptop_backup(self, client_name, os_type='windows', validate_logs=True, **kwargs):
        """This method runs the backup as Tenat or msp in adminmode for v2 laptops"""
        cloud_object = cloudlaptophelper.CloudLaptopHelper(self)
        cloud_utils = cloud_object.utils
        subclient_object = cloud_utils.get_subclient(client_name)
        job_status = cloud_object.check_if_any_job_running(client_name, subclient_object, os_type)
        if not job_status:
            raise Exception("Some issue with previous job and it is not completed successfully")
        #---rename the clbackup log file to validate backup status after job triggered --- #
        cloud_object.rename_backup_logfile(client_name, os_type)
        #------- BACKUP FROM ACTIONS--------#
        if kwargs.get('backup_type') == 'backup_from_actions':

            self.__rtable.access_action_item(client_name, 'Backup now')
            self.__admin_console.wait_for_completion()
            notification= self.__laptops.select_backuplevel_and_submit_backupjob(self.__backup.BackupType.INCR, v2_laptop=True)
            if 'Backup job started successfully' not in notification:                             
                raise CVWebAutomationException("Notification is not showing correctly when backup triggered for v2 Laptop")
        #------- BACKUP FROM DETAILS--------#
        elif kwargs.get('backup_type') == 'backup_from_detailspage':
            self.__rtable.access_link(client_name)
            self.__admin_console.click_button(value='Backup now')
            notification= self.__laptops.select_backuplevel_and_submit_backupjob(self.__backup.BackupType.INCR, v2_laptop=True)
            if 'Backup job started successfully' not in notification:                             
                raise CVWebAutomationException("Notification is not showing correctly when backup triggered for v2 Laptop")
        cloud_object.validate_immediate_backup(client_name, subclient_object, os_type, validate_logs)
        self.log.info("Cloud Laptop backup job triggered on client [{0}]".format(client_name))
        