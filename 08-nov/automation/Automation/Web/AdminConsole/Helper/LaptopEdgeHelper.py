# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to Laptop in Edgemode
LaptopEdgeMain : This class provides methods for Laptop related operations in edgemode

Class:

EdgeHelper()

Functions:

set_testcase_inputs()              -- Creates a dictionary for test case inputs needed for a 
                                        given test case for enduser operations.

validate_enduser_loggedin_url()    --  This method validates laptop owner logged in to edgemode or not

check_laptop_backup_mode()         -- This method validates whether given client is installed in v1 or v2 mode 

verify_client_exists_or_not()      -- This method verify enduser able to see his laptops as owner in edge mode or not 

trigger_v1_laptop_backup()         -- This method is used to run the v1 laptop backup   

trigger_v2_laptop_backup()         -- This method is used to run the v2 laptop backup   

subclient_restore_as_enduser()     -- This method is used to do the restore and perform restore validation 

trigger_backupjob()                -- This method Run the backup job after content added to subclient

validate_settings_page_summary_tile() -- this method validates summary tile information from settings page

validate_listing_page_in_edgemode()   -- This method validates the listing page details

validate_share_details_as_owner       -- This method is used to validate shares data as owner

validate_share_details_as_recepient   -- This method is used to validate shares data as recepient

validate_deleted_share                --  This method is used to validate shares after deleted

"""
import datetime
import math
import inspect
import re
from AutomationUtils import logger
from Web.AdminConsole.Laptop.LaptopEdgeMode import EdgeMain, EdgeSettings, EdgeRestore, EdgeShares
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Laptop import laptopconstants as lc
from AutomationUtils.config import get_config
from Web.AdminConsole.Helper.LaptopHelper import LaptopMain
from Server.JobManager.jobmanager_helper import JobManager
from Web.AdminConsole.Components.panel import RPanelInfo
from Laptop.CloudLaptop import cloudlaptophelper
from Web.Common.exceptions import CVWebAutomationException

class EdgeHelper:
    """Commandcenter helper for enduser operations in Edge mode"""

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
        self.__navigator = admin_page.navigator
        self.__edgemain = EdgeMain(admin_page)
        self.__utility = OptionsSelector(commcell)
        self.__edgerestore = EdgeRestore(admin_page)
        self.__edge_settings = EdgeSettings(admin_page)
        self.__edge_shares = EdgeShares(admin_page)
        self.__jobs = Jobs(self.__admin_console)
        self.__job_manager = JobManager(commcell=commcell)
        self.__laptop_obj = LaptopMain(admin_page, commcell)
        self.__edgemain_obj = EdgeMain(admin_page)
        self.__ida_utils = CommonUtils(commcell)
        self.log = logger.get_log()
        self._cloud_object = None
        self._source_dir = None
        self._client_name = None
        self._enduser = None
        self._source_dir = None
        self._machine_object = None
        self._activation_plan = None
        self._os_type = None
        self._configuration_status = 'Active'
        self._sla_status = 'Met'
        self._self_service = 'mode=eu#/devices?mode=edgeMode'
        self._edge_mode = 'mode=edgeMode'

    @property
    def os_type(self):
        """ Get os_type"""
        return self._os_type

    @os_type.setter
    def os_type(self, value):
        """ Set os_type"""
        self._os_type = value
        
    @property
    def client_name(self):
        """ Get client_name"""
        return self._client_name

    @client_name.setter
    def client_name(self, value):
        """ Set client_name"""
        self._client_name = value

    @property
    def enduser(self):
        """ Get enduser"""
        return self._enduser

    @enduser.setter
    def enduser(self, value):
        """ Set enduser"""
        self._enduser = value
    
    @property
    def source_dir(self):
        """ Get source data directory"""
        return self._source_dir
    
    @source_dir.setter
    def source_dir(self, value):
        """ Set source data directory"""
        self._source_dir = value
        
    @property
    def machine_object(self):
        """ Get machine_object"""
        return self._machine_object

    @machine_object.setter
    def machine_object(self, value):
        """ Set machine_object"""
        self._machine_object = value

    #---------------------------------------------------------------------------------------------
    # For most of the Commandcenter Testcases input is not taking from the End-User and 
    # input is reading from Config file. All inputs need to be provided in Config file
    #-------------------------------------------------------------------------------------
    @staticmethod
    def set_testcase_inputs(testcase, acl=False):
        """
            Creates a dictionary for test case inputs needed for a given test case for Laptop in edgemode.

        Args:
            testcase (obj):   Testcase object

        Returns:

            inputs (dict):    Key value dictionary for the required inputs for testcase fetched from constants

        Raises
            Exception:
                - If failed to get the inputs

        """
        inputs = {}
        try:
                
            platform = testcase.tsName.lower().split('_')[1].capitalize()
            Edge_config = get_config().Laptop
            if platform.lower() == 'windows':
                inputs['os_type'] = 'Windows'
                inputs['osc_options'] = None
            else:
                inputs['os_type'] = 'Mac'
                inputs['osc_options'] = '-testuser root -testgroup admin'

            if acl is True:
                user_inputs = Edge_config._asdict()['ACL']._asdict()
                os_map = user_inputs[platform]._asdict()
                machine_config = user_inputs[platform]._asdict()
                inputs["Client_name"] = os_map.get("Client_name", machine_config.get("Client_name"))
            else:
                user_inputs = Edge_config._asdict()['EdgeMode']._asdict()
                os_map = user_inputs[platform]._asdict()
                inputs["Edge_username"] = user_inputs["Edge_username"]
                inputs["Edge_password"] = user_inputs["Edge_password"]
                inputs["Default_Plan"] = user_inputs["Default_Plan"]
                inputs["Tenant_admin"] = user_inputs["Tenant_admin"]
                inputs["Tenant_password"] = user_inputs["Tenant_password"]
                inputs["Private_share_recepient_username"] = user_inputs["Private_share_recepient_username"]
                inputs["Private_share_recepient_password"] = user_inputs["Private_share_recepient_password"]
                inputs["Share_view_access_type"] = user_inputs["Share_view_access_type"]
                inputs["Share_edit_access_type"] = user_inputs["Share_edit_access_type"]
                inputs["Share_never_expire"] = user_inputs["Share_never_expire"]
                inputs["Share_expire_days"] = user_inputs["Share_expire_days"]
                machine_config = user_inputs[platform]._asdict()
                inputs["Machine_host_name"] = os_map.get("Machine_host_name", machine_config.get("Machine_host_name"))
                inputs["Client_name"] = os_map.get("Client_name", machine_config.get("Client_name"))
                inputs["Machine_user_name"] = os_map.get("Machine_user_name", machine_config.get("Machine_user_name"))
                inputs["Machine_password"] = os_map.get("Machine_password", machine_config.get("Machine_password"))
                inputs["Test_data_path"] =  os_map.get("Test_data_path", machine_config.get("Test_data_path"))
                inputs["Monikers_data_path"] =  os_map.get("Monikers_data_path", machine_config.get("Monikers_data_path"))
                inputs["Preview_Folder_path"] =  os_map.get("Preview_Folder_path", machine_config.get("Preview_Folder_path"))

            return inputs

        except KeyError as _:
            raise Exception("Failed to fetch inputs from config.json for {0} and {1}".format('EdgeMode', platform))
        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))
        
    @staticmethod
    def extarct_job_id_from_text(notification_text):
        """
        Args:
            notification_text (str): notification text

        Returns:

            jobid (str): jobid from give text message

        """

        job_id = re.findall(r'\d+', notification_text)[0]
        return job_id

    def check_laptop_backup_mode(self, tcinputs):
        """ This method is used to identify the given client is v1 laptop or v2 laptop"""

        client_obj = self.__utility.get_machine_object(tcinputs["Client_name"])
        tcinputs['client_object']=client_obj
        backup_mode = self.__utility.check_reg_key(client_obj, 'MediaAgent', "LaptopBackupMode")
        if str(backup_mode)=='2':
            tcinputs['Cloud_direct']=True
            self.log.info("----- Laptop is installed in cloud mode-----")
        else:
            tcinputs['Cloud_direct']=False
            self.log.info("----- Laptop is installed in classic mode-----")
        return tcinputs

    def validate_enduser_loggedin_url(self, metallic=False):
        """ This method is used to verify enduser logged in correctly into edge mode or not"""
        if metallic:
            current_url = self.__driver.current_url.split("commandcenter")[1]
            if self._self_service in current_url :
                self.log.info("Enduser logged into edge mode with self-service navigation")
            
            else:
                raise CVWebAutomationException("User {0} logged in URL is not correct {1}"\
                                                .format(self._enduser, current_url))
        else:
            self.__navigator.navigate_to_devices_edgemode()
            current_url = self.__driver.current_url.split("commandcenter")[1]
            if self._edge_mode in current_url:
                self.log.info("User logged into Edgemode successfully")
            
            else:
                raise CVWebAutomationException("User {0} logged in URL is not correct {1}"\
                                                .format(self._enduser, current_url))
   
    def verify_client_exists_or_not(self, input_client):
        """
        verify enduser able to see all his laptops in edgemode

        Args:

            input_clients (list /str)    --  list of clients given as inputs to the testcase

            console_clients (list)  --  list of clients visible in edgemode

        """
        if isinstance(input_client, str):
            input_client = [input_client]
        console_clients = self.__edgemain.get_client_names()
        for each_client in input_client:
            if each_client in console_clients:
                self.log.info("As enduser able to see the given clients")
            else:
                raise CVWebAutomationException("None of the clients found from laptop page in edge mode")

    def verify_any_backup_running(self):
        """
        Verify if any backup is running on client machine.
        """
        for _i in range(1, 6):
            status = self.__edge_settings.is_backup_running()
            if not status: 
                return 0
            self.log.info("backup job running.Will wait about 5 minutes to let job finish")
            self.__utility.sleep_time(120, "Waiting for Backup job to finish")
        raise CVWebAutomationException("Backup did not finish in 10 minutes. Exiting")

    def trigger_v1_laptop_backup(self, client_name):
        """This method runs the backup as enduser in edgmode for v1 laptop"""
        self.__edgemain.navigate_to_client_settings_page(client_name)
        self.verify_any_backup_running()
        job_id = self.__edge_settings.click_on_backup_button()  # Trigger the backup
        self.log.info("backup job [{0}] triggered on client [{1}]".format(job_id, client_name))
        jobobj = self.commcell.job_controller.get(job_id=job_id)
        self.__job_manager.job = jobobj
        self.__job_manager.wait_for_state('completed')
        
    def trigger_v2_laptop_backup(self, client_name, os_type='windows', validate_logs=True):
        """This method runs the backup as enduser in edgmode for v2 laptops"""
        self._cloud_object = cloudlaptophelper.CloudLaptopHelper(self)
        cloud_utils = self._cloud_object.utils
        subclient_object = cloud_utils.get_subclient(client_name)
        self.__edgemain.navigate_to_client_settings_page(client_name)
        job_status = self._cloud_object.check_if_any_job_running(client_name, subclient_object)
        if not job_status:
            raise Exception("Previous job stuck and not completed")
        #---rename the clbackup log file to validate backup status after job triggered --- #
        self._cloud_object.rename_backup_logfile(client_name)
        self.__edge_settings.click_on_backup_button_for_v2()  # Trigger the backup
        self._cloud_object.validate_immediate_backup(client_name, subclient_object, os_type, validate_logs)
        self.log.info("Cloud Laptop backup job triggered on client [{0}]".format(client_name))


    def subclient_restore_as_enduser(self, tmp_path=None, cleanup=True, navigate_to_sourcepath=True):
        """validate laptop restore"""
        try:
            if tmp_path is None:
                dest_path = self.__utility.create_directory(self._machine_object)
            else:
                dest_path = tmp_path
    
            compare_source = self._source_dir
            compare_destination = dest_path
            if not self._machine_object.os_info == 'WINDOWS':
                self._machine_object.change_file_permissions(dest_path, 775)
                self._machine_object.change_file_permissions(compare_source, 775)
                
            self.log.info(
                """
                Starting restore with source:[{0}],
                destination:[{1}],
                as enduser : [{2}]
                """.format(self._source_dir, dest_path, self._enduser)
                )
            restore_job_id = self.__edgerestore.browse_and_restore(self._source_dir, dest_path, navigate_to_sourcepath)
    
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
                
    def trigger_backupjob(self, tcinputs):
        """ Auto trigger backup job when subclient content added"""

        # Add new content with required size to default subclient of this client and run incremental backup
        options=tcinputs["osc_options"]
        self.log.info("Add new content with required size and run the incremental job on this client")
        subclient_obj = self.__ida_utils.get_subclient(self._client_name)
        
        if options is None:
            self._source_dir = tcinputs['Test_data_path'] + "\\" + 'TC_Data'
        else:
            self._source_dir = tcinputs['Test_data_path'] + "/" + 'TC_Data'
        
        self.__utility.create_test_data(self._machine_object, self._source_dir, options=options)
        #content_size = int(self._machine_object.get_folder_size(self._source_dir))
        _obj = self.__ida_utils.subclient_backup(subclient_obj, wait=False)

        jobs = self.__job_manager.get_filtered_jobs(
            self._client_name,
            time_limit=30,
            retry_interval=5,
            backup_level='Incremental',
            current_state='Running'
            )
        jobid = jobs[1][0]
        jobobj = self.commcell.job_controller.get(job_id=jobid)
        #------last backup size of the incr bakup job
        full_job_details = jobobj.details

        sub_dict = full_job_details['jobDetail']['detailInfo']
        lastbackupsize =  int(sub_dict.get('sizeOfApplication'))
        #-----get the Last backup size from last job convert to adminconsole display format--------#
        #----------- Read the folder size which intern returns in "MB"---------#
        #backup_content_size = int(self._machine_object.get_folder_size(self._source_dir))
        self.log.info("get the last backup size from last backup job ")
        last_backup_size = self.__laptop_obj.covert_size_to_mb(lastbackupsize, 'bytes')

        #return jobobj, jobid, content_size
        return jobobj, jobid, last_backup_size

    def validate_settings_page_summary_tile(self, plan_name, tcinputs=None, cleanup=True):
        """Laptop settings page summary tile validation"""
        
        try:
            self.__edgemain_obj.navigate_to_client_settings_page(self._client_name)
            summary_dict = RPanelInfo(self.__admin_console, 'Summary').get_details()
            backup_info = {}
            backup_size_unit = summary_dict['Application size'].split()
            backup_size = backup_size_unit[0]
            backup_units = backup_size_unit[1]
            #------- convert the backup size into "MB" --------#
            current_total_backup = self.__laptop_obj.covert_size_to_mb(backup_size, backup_units)

            jobobj, _joid, last_backup_size = self.trigger_backupjob(tcinputs)
            #----------- Read the folder size which intern returns in "MB"---------#
            backup_info['Application size'] = current_total_backup + last_backup_size
            self.log.info("Current application size {0} and folder size {1}".format(current_total_backup, last_backup_size))
            #----------- read the last backup time and size from above triggered job --------#
            full_job_details = jobobj.details
            sub_dict = full_job_details['jobDetail']['detailInfo']
            backup_info['Last backup time'] = sub_dict.get('startTime')
            backup_info['Last Backup Size'] = int(sub_dict.get('sizeOfApplication'))
            backup_info['Last job status'] = jobobj.status
            
    
            backup_time = datetime.datetime.fromtimestamp(int(backup_info['Last backup time']))
            last_backup_time = backup_time.strftime('%b %#d, %#I:%M %p')
            clientobject = self.commcell.clients.get(self._client_name)
            client_details = self.__laptop_obj.get_client_details(clientobject, client_region=True)
            #-----get the Last backup size from last job convert to adminconsole display format--------#
            self.log.info("get the last backup size from last backup job ")
            last_backup_size_before_convertion = backup_info['Last Backup Size']
            last_backupsize_after_conversion = self.__laptop_obj.covert_size_to_mb(last_backup_size_before_convertion, 'bytes')
            i = int(math.floor(math.log(last_backupsize_after_conversion, 1024)))
            power = math.pow(1024, i)
            last_backupsize = round(last_backupsize_after_conversion / power, 2)
            
            summary_validation_dict = {
             'Host name':self._client_name,
             'Last backup time':last_backup_time,
             'Last backup size':last_backupsize,
             'Application size':backup_info['Application size'],
             'Configuration status':self._configuration_status ,
             'Last seen online':client_details['Last online time'],
             #'Next backup time':,
             'Plan':plan_name,
             'Workload region':client_details['Workload region']
             }
            
            #read latest data from summary tile after inc job
            self.__driver.refresh()
            self.__admin_console.wait_for_completion()
            summary_dict = RPanelInfo(self.__admin_console, 'Summary').get_details()
            laptop_summary_dict = RPanelInfo(self.__admin_console, 'Summary').get_details()
            
            #----------- validation of the data from laptop summary tile--------#
            for dict_key, dict_val in summary_validation_dict.items():
                self.log.info('validation values "{0}"'.format(dict_val))
                if dict_key == 'Application size':
                    #------- convert the current Application size into "MB" --------#
                    total_backupsize_before_convertion = laptop_summary_dict[dict_key]
                    temp_sizeunit_list = total_backupsize_before_convertion.split()
                    backup_size = temp_sizeunit_list[0]
                    backup_units = temp_sizeunit_list[1]
                    total_backupsize_after_convertion = self.__laptop_obj.covert_size_to_mb(backup_size, backup_units)
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
                    last_backup_size_after_conversion = self.__laptop_obj.covert_size_to_mb(backup_size, backup_units)
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
                else:
                    if dict_val == laptop_summary_dict[dict_key]:
                        self.log.info("displayed value {0} matches with given value {1}".format(
                            laptop_summary_dict[dict_key], dict_val))
            
                    else:
                        exp = "displayed value {0} does not match with given value {1} for column: {2}".format(
                            laptop_summary_dict[dict_key], dict_val, dict_key)
                        raise Exception(exp)
        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))
        finally:
            if cleanup:
                self.__utility.remove_directory(self._machine_object, self._source_dir)

    def validate_listing_page_in_edgemode(self, tcinputs=None, cleanup=True):
        """validates the laptop listing page details after every incr data"""
        
        try:
            backupsize_and_time = {}
            self.__laptop_obj.client_name = self._client_name
            self.__laptop_obj.machine_object = self._machine_object
            jobobj, _joid, _size = self.trigger_backupjob(tcinputs)
            #----------- read the last backup time and size from above triggered job --------#
            full_job_details = jobobj.details
            sub_dict = full_job_details['jobDetail']['detailInfo']
            backupsize_and_time['Last backup time'] = sub_dict.get('startTime')
            backupsize_and_time['Last Backup Size'] = int(sub_dict.get('sizeOfApplication'))
            backupsize_and_time['Last job status'] = jobobj.status
    
            backup_time = datetime.datetime.fromtimestamp(int(sub_dict.get('startTime')))
            last_backup_time = backup_time.strftime('%b %#d, %Y, %#I:%M:%S %p')
            #-----get the Last backup size from last job convert to adminconsole display format--------#
            last_backup_size_before_convertion = int(sub_dict.get('sizeOfApplication'))
            last_backupsize_after_conversion = self.__laptop_obj.covert_size_to_mb(last_backup_size_before_convertion, 'bytes')
            i = int(math.floor(math.log(last_backupsize_after_conversion, 1024)))
            power = math.pow(1024, i)
            last_backupsize = round(last_backupsize_after_conversion / power, 2)
    
        
            listing_validation_dict = {
               'Last backup time': last_backup_time,
               'Last job status': jobobj.status,
               'Last backup size': last_backupsize,
               #'Next backup time':None
               'SLA status': self._sla_status 
            }
        
            #read latest data from listing after inc job
            self.__driver.refresh()
            self.__admin_console.wait_for_completion()
            table_data = self.__edgemain_obj.get_client_data(self._client_name)
            
            #----------- validation of the data from laptop listing page--------#
            for dict_key, dict_val in listing_validation_dict.items():
                
                if dict_key == 'Last backup size':
                    disp_val = table_data[dict_key]
                    key_val = dict_val
                    #------- convert the Last backup size into "MB" --------#
                    temp_sizeunit_list = disp_val.split()
                    backup_size = temp_sizeunit_list[0]
                    backup_units = temp_sizeunit_list[1]
                    last_backup_size_after_conversion = self.__laptop_obj.covert_size_to_mb(backup_size, backup_units)
                    i = int(math.floor(math.log(last_backup_size_after_conversion, 1024)))
                    power = math.pow(1024, i)
                    last_backup_size = round(last_backup_size_after_conversion / power, 2)
                    if last_backup_size == key_val:
                        self.log.info("'{0}' displayed value '{1}' match with validation value '{2}'"
                                        .format(disp_val, last_backup_size, key_val))
                    else:
                        exp = "Last backup size {0} not updated correctly ".format(
                           listing_validation_dict['dict_key'])
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
            if cleanup:
                self.__utility.remove_directory(self._machine_object, self._source_dir)
    
    
    def validate_share_details_as_owner(self, folder_name, share_path, share_created_time, expire_selection='Never'):
        """This method is used to validate shares data as owner
        
        Args:

            folder_name(str)     --  Folder name which has been shared 

            share_path(str)      --  Path of the shared folder 
            
            share_created_time() --  Recorded time while creating private share 
            
            expire_selection()   --  Expire option selected while creating share 

        """
        shares_info= self.__edge_shares.read_shared_by_me_data()
        if not shares_info:
            raise CVWebAutomationException("Unable to read the data from shares page")
        
        item_found = 0
        for each_item in shares_info:
            if each_item['Name']==folder_name and each_item['Source']==self._client_name:
                self.log.info("Shared Name and client Name is showing correct")
                item_found=1
                #--path and client name validation
                if each_item['Path']==share_path: 
                    self.log.info("Shared path is showing correctly")
                else:
                    raise CVWebAutomationException("shared file path not correct {0}" .format(each_item['Path']))
                #--share created date validation
                display_time_object = datetime.datetime.strptime(each_item['Date Created'], '%b %d, %Y %I:%M:%S %p')
                share_craeted_time_object = datetime.datetime.strptime(share_created_time, '%b %d, %Y %I:%M:%S %p')
                if display_time_object > share_craeted_time_object:
                    self.log.info("Share created time is showing correct")
                else:
                    exp = "Shared file date is not showing correct date {0} ".format(each_item['Date Created'])
                    self.log.exception(exp)
                    raise Exception(exp)   
                #--share expiry validation
                if each_item['Expiry'] == expire_selection:
                    self.log.info("Share expiry is showing correctly")
                else:
                    raise CVWebAutomationException("Shared file expire is not showing correct{0}" .format(each_item['Expiry']))
                
        if item_found == 0:
            raise CVWebAutomationException("Unable to find the shared folder name {}" .format(folder_name))
        
    def validate_share_details_as_recepient(self, folder_name, owner_name, share_created_time, expire_selection='Never'):
        """This method is used to validate shares data as recepient
        
        Args:

            folder_name(str)     --  Folder name which has been shared 

            recepient_name(str)  --  recepient user name
            
            share_created_time() --  Recorded time while creating private share 
            
            expire_selection()   --  Expire option selected while creating share 

        """
        shares_info= self.__edge_shares.read_shared_with_me_data()
        item_found = 0
        if not shares_info:
            raise CVWebAutomationException("Unable to read the data from shares page")
        for each_item in shares_info:
            if each_item['Name']==folder_name:
                self.log.info("Shared Name is showing correct")
                item_found=1
                #--share owner name validation
                if each_item['Owner']==owner_name: 
                    self.log.info("Shared owner is showing correctly")
                else:
                    raise CVWebAutomationException("Shared Owner is not showing correct {0}" .format(each_item['Owner']))
                #--share created date validation
                display_time_object = datetime.datetime.strptime(each_item['Date Created'], '%b %d, %Y %I:%M:%S %p')
                share_craeted_time_object = datetime.datetime.strptime(share_created_time, '%b %d, %Y %I:%M:%S %p')
                if display_time_object > share_craeted_time_object:
                    self.log.info("Share created time is showing correct")
                else:
                    exp = "Shared file date is not showing correct date {0} ".format(each_item['Date Created'])
                    self.log.exception(exp)
                    raise Exception(exp)   

                #--share expiry validation
                if each_item['Expiry'] == expire_selection:
                    self.log.info("Share expiry is showing correctly")
                else:
                    raise CVWebAutomationException("Shared file expire is not showing correct{0}" .format(each_item['Expiry']))
                
        if item_found == 0:
            raise CVWebAutomationException("Unable to find the shared folder name {0}" .format(folder_name))
        
    def validate_deleted_share(self, folder_name):
        """This method is used to validate shares after deleted
        
        Args:

            folder_name(str)     --  Folder name which has been shared 

        """
        shares_info= self.__edge_shares.read_shared_by_me_data()
        for each_item in shares_info:
            if each_item['Name']==folder_name and each_item['Source']==self._client_name:
                raise CVWebAutomationException("Shared folder still showing even after share delted {}" .format(folder_name))
        self.log.info("As expected ! shared folder not showing after deleted")

    def validate_publicshare_details(self, folder_name, share_created_time):
        """This method is used to validate shares data as recepient
        
        Args:

            folder_name(str)     --  Folder name which has been shared 

            share_created_time --  Recorded time while creating private share 
            
            file_name   --  File name which has been shared

        """
        shares_info= self.__edge_shares.read_publicshare_data()
        item_found = 0
        if not shares_info:
            raise CVWebAutomationException("Unable to read the data from shares page")
        for each_item in shares_info:
            if each_item['Name']==folder_name:
                self.log.info("Shared Folder Name is showing correct")
                item_found=1
                #--share created date validation
                display_time_object = datetime.datetime.strptime(each_item['Date Modified'], '%b %d, %Y %I:%M:%S %p')
                share_craeted_time_object = datetime.datetime.strptime(share_created_time, '%b %d, %Y %I:%M:%S %p')
                if display_time_object > share_craeted_time_object:
                    self.log.info("Share created time is showing correct")
                else:
                    exp = "Shared file date is not showing correct date {0} ".format(each_item['Date Created'])
                    self.log.exception(exp)
                    raise Exception(exp)
                #--share Size validation
                if each_item['Size'] != 0:
                    self.log.info("Share Size is showing correctly")
                else:
                    raise CVWebAutomationException("Shared file Size is not showing correct{0}" .format(each_item['Size']))
         
        if item_found == 0:
            raise CVWebAutomationException("Unable to find the shared folder name {0}" .format(folder_name))